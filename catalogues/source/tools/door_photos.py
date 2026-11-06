"""The door photographs for the door catalogue: each supplied picture of a door's front, trimmed to the door with a
small margin, its white (or transparent) ground multiplied into the catalogue's paper (#F4F3F0), at the size it came
in. The same pictures, in the same colours, as the website's (img/doors, made 800 x 1000 from these): the PDF needs
them larger. Five models came without photographs (PT 109, 409, 709, 809 and 909): their pictures are the price
list's own, which are small (some 370 px tall); they are kept at that size here, and enlarged only where they are
placed (prepare_doors.py).
    python3 -I door_photos.py <supplied photographs dir> <price list pictures dir> <out dir>
The supplied photographs are numbered as they were sent (001.webp ...); the price list's pictures as pdfimages
writes them (x-000.png ...)."""
import os
import sys
import numpy as np
from PIL import Image

raw, pdf, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
PLATE = np.array([0xF4, 0xF3, 0xF0], float) / 255.0
MARGIN = 0.02      # of the door's height, on every side


def pdf_img(n, mask=None):
    im = Image.open(os.path.join(pdf, "x-%03d.png" % n)).convert("RGB")
    if mask is not None:
        m = Image.open(os.path.join(pdf, "x-%03d.png" % mask)).convert("L").resize(im.size)
        im = im.convert("RGBA")
        im.putalpha(m)
    return im


def user_img(name):
    return Image.open(os.path.join(raw, name))


JOBS = []  # (slug, image)


def tri_user(start, key, order):
    for i, c in enumerate(order):
        JOBS.append((key + "-" + c, user_img("%03d.webp" % (start + i))))


def tri_pdf(key, pairs):
    for c, n, m in pairs:
        JOBS.append((key + "-" + c, pdf_img(n, m)))


# as sent: red is the price list's Brown, grey its Dark Grey (the website's img/doors were made the same way)
O = ["brown", "white", "dark-grey"]
tri_user(1, "pt-110", O)
tri_user(4, "pt-111", O); tri_user(7, "pt-112", O); tri_user(10, "pt-113", O); tri_user(13, "pt-114", O); tri_user(16, "pt-115", O)
tri_user(19, "pt-116", ["dark-grey", "brown", "white"]); tri_user(22, "pt-117", O); tri_user(25, "pt-118", O)
tri_user(28, "pt-119", ["dark-grey", "brown", "white"]); tri_user(31, "pt-270", O); tri_user(34, "pt-290", ["dark-grey", "brown", "white"])
for n, s in [(38, "dark-grey-white-list"), (41, "dark-grey-black-list"), (42, "brown-white-list"), (45, "brown-black-list"),
             (47, "white-white-list"), (48, "white-black-list")]:
    JOBS.append(("pt-2601-" + s, user_img("%03d.webp" % n)))
for n, s in [(50, "dark-grey-white-list"), (53, "dark-grey-black-list"), (55, "brown-white-list"), (56, "white-black-list"),
             (57, "white-white-list"), (58, "brown-black-list")]:
    JOBS.append(("pt-2602-" + s, user_img("%03d.webp" % n)))
tri_pdf("pt-109", [("dark-grey", 0, None), ("brown", 1, None), ("white", 2, None)])
tri_pdf("pt-409", [("white", 92, None), ("dark-grey", 93, None), ("brown", 94, None)])
tri_pdf("pt-709", [("white", 95, 96), ("brown", 97, 98), ("dark-grey", 99, 100)])
tri_pdf("pt-909", [("dark-grey", 103, None), ("brown", 104, None), ("white", 105, None)])
tri_pdf("pt-809", [("dark-grey", 106, None), ("brown", 107, None), ("white", 108, None)])

for slug, im in JOBS:
    a = np.array(im.convert("RGBA")).astype(float)
    alpha = a[..., 3:4] / 255.0
    rgb = a[..., :3] / 255.0 * alpha + (1 - alpha)
    if slug == "pt-2602-white-white-list":            # a stray blue dot in the supplied photograph, bottom right
        blue = (rgb[..., 2] - rgb[..., 0] > 0.2) & (rgb[..., 2] > 0.5)
        blue[: int(rgb.shape[0] * 0.85)] = False
        rgb[blue] = 1.0
    ys, xs = np.where(rgb.min(axis=2) < 0.94)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    m = int(round((y1 - y0) * MARGIN))
    canvas = np.ones((y1 - y0 + 2 * m, x1 - x0 + 2 * m, 3))
    canvas[m:m + y1 - y0, m:m + x1 - x0] = rgb[y0:y1, x0:x1]
    img = Image.fromarray((canvas * PLATE * 255).round().astype(np.uint8))
    img.save(os.path.join(out, slug + ".jpg"), "JPEG", quality=90, optimize=True, progressive=True)
print(len(JOBS), "photographs in", out)
