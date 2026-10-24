"""Prepare the catalogue's images: renders to JPEG, sink-centred thumbnails, swatches cropped from
the supplied product photographs, logos. Writes <out>/img/... and <out>/assets-<mode>.json.

    python prepare_assets.py <renders_dir> <photos_dir> <logos_dir> <out_dir> <print|screen>
"""
import json
import os
import sys
from PIL import Image

renders, photos, logos, out, mode = sys.argv[1:6]
PRINT = mode == "print"
Q = 90 if PRINT else 82
HERO_W = None if PRINT else 1700      # keep print renders at full size
COVER_W = None if PRINT else 1500

GRANITE = ["gdu8145", "gst6045", "gst7546", "gsu6045", "gsu7545", "gsu8045"]
STEEL = ["lps5040", "lps7540a", "lps8643a", "lps9643a", "lps10050a", "wl03", "wl05a", "wl07", "wl11", "wl12", "wl18",
         "w5050tsb", "w6045tss", "w6045tsb", "w7546tsb", "w7546tsbn", "w7646uss", "w7646usb", "w7845uds", "w7845udb",
         "w8050tss", "w8050tsb", "w8245tdb", "w8550tdg", "w10050tsg"]
# extra views (covers, intros, range openers, closing page); each falls back to a hero if not rendered
EXTRA = {"cover_granite": "gdu8145", "cover_stainless": "w7646uss", "intro_granite": "gsu7545", "intro_stainless": "w7546tsbn",
         "opener_pressed": "lps9643a", "opener_hand": "w8050tsb", "closing": "w5050tsb", "notes_stainless": "wl18", "index_granite": "gst6045"}
# the colour and finish pages: a detail of each from one of the kitchens (render, crop round the sink's own box)
DETAIL = {"colour": {"pearl": "gdu8145", "pure": "gsu7545", "titan": "gsu8045"},
          "finish": {"Mat Polished": "lps9643a", "Electroplate": "wl05a", "Satin": "w7646uss", "Nano Black": "w8050tsb"}}

sub = "img-print" if PRINT else "img-screen"
D = lambda *p: os.path.join(out, sub, *p)
R = lambda *p: "/".join([sub] + list(p))
for d in ("heroes", "thumbs", "products", "swatch", "finish", "extra"):
    os.makedirs(D(d), exist_ok=True)


def load(path):
    im = Image.open(path)
    if im.mode in ("I;16", "I;16B", "I"):
        im = im.point(lambda v: v / 256).convert("L")
    return im.convert("RGB")


def save(im, path, w=None):
    if w and im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(path, "JPEG", quality=Q, optimize=True, progressive=True, subsampling=0 if PRINT else 2)


def meta(name):
    p = os.path.join(renders, name + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def render_path(name):
    for ext in (".png", ".jpg"):
        p = os.path.join(renders, name + ext)
        if os.path.exists(p):
            return p
    return None


assets = {"granite": {}, "stainless": {}}
hero_pos = {}
heroes, thumbs = {}, {}
for name in GRANITE + STEEL:
    src = render_path(name)
    if not src:
        print("missing render", name)
        continue
    im = load(src)
    save(im, D("heroes", name + ".jpg"), HERO_W)
    heroes[name] = R("heroes", name + ".jpg")
    m = meta(name)
    bb = m["bbox"] if m else dict(x0=0.3, x1=0.7, y0=0.4, y1=0.75)
    cx, cy = (bb["x0"] + bb["x1"]) / 2, (bb["y0"] + bb["y1"]) / 2
    # the feature page's hero box keeps the full width: only the height is cropped; keep the sink in view
    box_aspect = (216 / 169) if PRINT else (210 / 166)
    vis = min(1.0, (im.width / im.height) / box_aspect)
    if vis < 1.0:
        top = min(max(cy - vis / 2, 0.0), 1 - vis)
        hero_pos[name] = f"center {top / (1 - vis) * 100:.1f}%"
    else:
        hero_pos[name] = "center"
    # thumbnail: the sink and a little of its setting, 1.4 : 1
    bw = (bb["x1"] - bb["x0"]) * im.width
    tw = min(im.width, bw * 1.75)
    th = tw / 1.4
    if th > im.height:
        th = im.height
        tw = th * 1.4
    x0 = min(max(cx * im.width - tw / 2, 0), im.width - tw)
    y0 = min(max(cy * im.height - th / 2, 0), im.height - th)
    t = im.crop((round(x0), round(y0), round(x0 + tw), round(y0 + th)))
    save(t, D("thumbs", name + ".jpg"), 900 if PRINT else 600)
    thumbs[name] = R("thumbs", name + ".jpg")

# product photographs, as supplied (on their plate)
products = {}
for f in sorted(os.listdir(photos)):
    if not f.endswith(".webp"):
        continue
    k = f[:-5]
    im = Image.open(os.path.join(photos, f)).convert("RGB")
    save(im, D("products", k + ".jpg"))
    products[k] = R("products", k + ".jpg")

# granite colour swatches: the bowl floor of the GSU 7545 in each colour, left of the waste
swatch, colour_prod = {}, {}
for cid, slug in (("pearl", "gsu-7545-pearl-black"), ("pure", "gsu-7545-pure-white"), ("titan", "gsu-7545-titanium-grey")):
    im = Image.open(os.path.join(photos, slug + ".webp")).convert("RGB")
    W, H = im.size
    crop = im.crop((int(W * 0.14), int(H * 0.49), int(W * 0.40), int(H * 0.75)))
    crop = crop.resize((900, 900), Image.LANCZOS)
    save(crop, D("swatch", cid + ".jpg"))
    swatch[cid] = R("swatch", cid + ".jpg")
    colour_prod[cid] = products[slug]

# stainless finish close-ups: the corner of a bowl in each finish (the same photographs the shop's site uses)
finish = {}
for f, slug, box in (("Mat Polished", "lps-7540-a", (0.68, 0.30, 0.92, 0.54)), ("Electroplate", "wl-07", (0.14, 0.26, 0.40, 0.52)),
                     ("Satin", "w-7646-uss", (0.56, 0.30, 0.86, 0.60)), ("Nano Black", "w-7646-usb", (0.56, 0.30, 0.86, 0.60))):
    im = Image.open(os.path.join(photos, slug + ".webp")).convert("RGB")
    W, H = im.size
    crop = im.crop((int(W * box[0]), int(H * box[1]), int(W * box[2]), int(H * box[3])))
    s = min(crop.size)
    crop = crop.crop((0, 0, s, s)).resize((800, 800), Image.LANCZOS)
    save(crop, D("finish", f.replace(" ", "-").lower() + ".jpg"))
    finish[f] = R("finish", f.replace(" ", "-").lower() + ".jpg")

# extra views
extra, extra_pos = {}, {}
for k, fallback in EXTRA.items():
    src = render_path(k) or render_path(fallback)
    if not src:
        continue
    im = load(src)
    save(im, D("extra", k + ".jpg"), COVER_W)
    extra[k] = R("extra", k + ".jpg")

# details for the colour and finish pages
details = {"colour": {}, "finish": {}}
os.makedirs(D("detail"), exist_ok=True)
for group, table in DETAIL.items():
    for key, name in table.items():
        src = render_path(name)
        if not src:
            continue
        im = load(src)
        m = meta(name)
        bb = m["bbox"] if m else dict(x0=0.3, x1=0.7, y0=0.4, y1=0.75)
        # a square-ish window on the middle of the sink, a little larger than half its width
        bw = (bb["x1"] - bb["x0"]) * im.width
        w = bw * (0.46 if group == "colour" else 0.6)
        h = w * (84 / 56 if group == "colour" else 58 / 87)
        cx = (bb["x0"] + bb["x1"]) / 2 * im.width
        cy = (bb["y0"] * 0.3 + bb["y1"] * 0.7) * im.height
        x0 = min(max(cx - w / 2, 0), im.width - w)
        y0 = min(max(cy - h / 2, 0), im.height - h)
        c = im.crop((round(x0), round(y0), round(x0 + w), round(y0 + h)))
        k = key.replace(" ", "-").lower()
        save(c, D("detail", f"{group}-{k}.jpg"), 1200 if PRINT else 700)
        details[group][key] = R("detail", f"{group}-{k}.jpg")

# the dark stone the dark text pages are laid on
stone = None
sp = render_path("stone_dark")
if sp:
    save(load(sp), D("extra", "stone_dark.jpg"), 1400 if not PRINT else None)
    stone = R("extra", "stone_dark.jpg")

# logos
os.makedirs(os.path.join(out, sub), exist_ok=True)
for name, f in (("logo-light", "LOGO_LIGHT.webp"), ("logo-ink", "LOGO_INK.webp")):
    Image.open(os.path.join(logos, f)).convert("RGBA").save(D(name + ".png"))
mark = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 216"><g fill="#ece7df">'
        '<polygon points="0,153 64,0 116,0 197,169 176,215 93,42 44,153"/>'
        '<polygon points="169,65 198,0 250,0 319,153 274,153 223,42 191,110"/></g></svg>')
open(D("mark-light.svg"), "w").write(mark)

common = dict(heroes=heroes, thumbs=thumbs, products=products, hero_pos=hero_pos, stone=stone,
              logo_light=R("logo-light.png"), logo_ink=R("logo-ink.png"), mark_light=R("mark-light.svg"))
assets["granite"] = dict(common, cover=extra.get("cover_granite"), intro=extra.get("intro_granite"), swatch=swatch, colour_prod=colour_prod,
                         colour_detail=details["colour"], strip=extra.get("index_granite"), cover_pos="center 60%", intro_pos="center 55%")
assets["stainless"] = dict(common, cover=extra.get("cover_stainless"), intro=extra.get("intro_stainless"), finish=finish,
                           finish_detail=details["finish"], strip=extra.get("notes_stainless"),
                           opener_pressed=extra.get("opener_pressed"), opener_hand=extra.get("opener_hand"), closing=extra.get("closing"),
                           cover_pos="center 60%", intro_pos="center 55%")
json.dump(assets, open(os.path.join(out, f"assets-{mode}.json"), "w"), indent=1)
print("assets:", len(heroes), "heroes,", len(products), "photos")
