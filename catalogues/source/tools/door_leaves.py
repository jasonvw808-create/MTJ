"""The website's Wellup Door Hall: each door's leaf, cut from its photograph and straightened.

Every door photograph (catalogues/images/doors/<slug>.jpg — the shop's photograph of each model in each colour, the
door standing in its frame on a light plate) gives:
  img/doors/leaf/<slug>.webp     the leaf alone: cut inside the frame, its four corners warped to an upright
                                 rectangle of the listed 70 x 200 cm (700 x 2000 px), the background gone with the
                                 frame round it (the leaf fills the picture to its edges, so the WebP needs no alpha
                                 and is written opaque)
  img/doors/leaf/t/<slug>.webp   the same, small (84 x 240), for the Door Hall's rail of models
and leaf.json beside them: per door the colour of its leaf's edge and of its frame, sampled from the photograph (the
3D door's edges and frame are drawn in them), the leaf's measured width ÷ height in the photograph and its height in
pixels there (how much detail the texture really has).

Finding the leaf, on luminance profiles taken along the door:
  · the frame's outer edges — the first run of pixels off the plate — high and low on the door, so a photograph that
    leans keeps its frame widths true;
  · the seam between frame and leaf — the deepest point of the dark band inside the frame (the rebate and the gap
    behind the leaf); the leaf begins just past it;
  · the four frame widths (left, right, high, low) are checked against each other, and one that disagrees with the
    rest takes theirs; a photograph whose frame disagrees with the other colours of its model (renders of one door)
    takes theirs;
  · the head seam the same way, about a frame-width below the top;
  · the foot: just above the dark line of shadow beneath the door.
The warp reads the photograph enlarged twice (Lanczos) and resamples once (bicubic), then sharpens a little. The
photographs are 330 to 1430 px tall at the leaf, so a 2000 px texture is an enlargement: it cannot hold more detail
than the photograph. The pictures draw most leaves wider than 70:200 (about 0.38-0.42); the warp brings each to the
listed 70 x 200 cm.

    python3 door_leaves.py <photos dir> <img/doors/leaf dir>        (Pillow and NumPy)"""
import json
import os
import re
import sys

import numpy as np
from PIL import Image, ImageFilter

LEAF_W, LEAF_H, THUMB_W, THUMB_H = 700, 2000, 84, 240


def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def first_off_plate(p, plate, rng, tol=4.0, run=3):
    rng = list(rng)
    for i, x in enumerate(rng):
        if all(abs(p[rng[j]] - plate) > tol for j in range(i, min(i + run, len(rng)))):
            return x
    return rng[0]


def deepest(p, a, b):
    a, b = max(int(a), 1), min(int(b), len(p) - 1)
    seg = p[a:b]
    m = seg.min()
    xs = [a + i for i, v in enumerate(seg) if v <= m + 0.5]
    run = [xs[0]]
    for x in xs[1:]:
        if x == run[-1] + 1:
            run.append(x)
        else:
            break
    return (run[0] + run[-1]) / 2.0


def measure(a):
    L = lum(a)
    h, w = L.shape
    plate = float(np.median(np.concatenate([L[:3, :].ravel(), L[:, :3].ravel(), L[:, -3:].ravel()])))
    colp = L[int(h * 0.2):int(h * 0.8), :].mean(axis=0)
    X0 = first_off_plate(colp, plate, range(0, w // 3))
    X1 = first_off_plate(colp, plate, range(w - 1, 2 * w // 3, -1)) + 1
    W = X1 - X0
    rowp = L[:, X0 + int(W * 0.3):X0 + int(W * 0.7)].mean(axis=1)
    y0 = first_off_plate(rowp, plate, range(0, h // 4))
    yend = first_off_plate(rowp, plate, range(h - 1, 3 * h // 4, -1)) + 1
    H = yend - y0
    ymin = int(round(deepest(rowp, max(y0, yend - int(H * 0.07)), yend)))
    door = float(np.median(rowp[max(y0, ymin - int(H * 0.05)):max(y0 + 1, ymin - int(H * 0.012))]))
    half = (door + rowp[ymin]) / 2
    yb = ymin
    while yb > ymin - int(H * 0.03) and ((rowp[yb] < half) if door > rowp[ymin] else (rowp[yb] > half)):
        yb -= 1
    out = {"W": W, "y0": y0, "yb": float(yb), "H": H, "bands": {}}
    for k, (r0, r1) in {"hi": (y0 + H * 0.12, y0 + H * 0.36), "lo": (y0 + H * 0.60, y0 + H * 0.86)}.items():
        p = L[int(r0):int(r1), :].mean(axis=0)
        x0 = first_off_plate(p, plate, range(0, w // 3))
        x1 = first_off_plate(p, plate, range(w - 1, 2 * w // 3, -1)) + 1
        lo, hi = int(W * 0.025), int(W * 0.17)
        out["bands"][k] = {"x0": x0, "x1": x1, "fl": deepest(p, x0 + lo, x0 + hi) - x0, "fr": x1 - deepest(p, x1 - hi, x1 - lo),
                           "y": (r0 + r1) / 2}
    return out, L


def leaf_quad(m, L):
    f = m["f"]
    hi, lo = m["bands"]["hi"], m["bands"]["lo"]
    W = hi["x1"] - hi["x0"]
    tops = []
    for c0, c1 in ((hi["x0"] + int(W * 0.28), hi["x0"] + int(W * 0.45)), (hi["x0"] + int(W * 0.55), hi["x0"] + int(W * 0.72))):
        p = L[:, c0:c1].mean(axis=1)
        tops.append((deepest(p, m["y0"] + f * 0.4, m["y0"] + f * 1.8 + 2), (c0 + c1) / 2))
    if abs(tops[0][0] - tops[1][0]) > max(0.3 * f, 4):
        t = (tops[0][0] + tops[1][0]) / 2
        tops = [(t, tops[0][1]), (t, tops[1][1])]
    g = 1.5
    lxh, lxl = hi["x0"] + hi["fl"] + g, lo["x0"] + lo["fl"] + g
    rxh, rxl = hi["x1"] - hi["fr"] - g, lo["x1"] - lo["fr"] - g
    lb = (lxl - lxh) / (lo["y"] - hi["y"]); la = lxh - lb * hi["y"]
    rb = (rxl - rxh) / (lo["y"] - hi["y"]); ra = rxh - rb * hi["y"]
    (t1, c1), (t2, c2) = tops
    tb = (t2 - t1) / (c2 - c1); ta = t1 + g - tb * c1
    def top_at(a, b):
        y = (ta + tb * a) / (1 - tb * b)
        return [a + b * y, y]
    yb = m["yb"]
    return [top_at(la, lb), top_at(ra, rb), [ra + rb * yb, yb], [la + lb * yb, yb]]


def persp(quad, w, h):
    dst = [(0, 0), (w, 0), (w, h), (0, h)]
    A, B = [], []
    for (x, y), (u, v) in zip(dst, quad):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def hexof(rgb):
    return "#" + "".join(f"{int(round(v)):02X}" for v in rgb)


def main(src, dst):
    os.makedirs(os.path.join(dst, "t"), exist_ok=True)
    names = sorted(f[:-4] for f in os.listdir(src) if f.endswith(".jpg"))
    imgs, M, Ls = {}, {}, {}
    for n in names:
        imgs[n] = Image.open(os.path.join(src, n + ".jpg")).convert("RGB")
        M[n], Ls[n] = measure(np.asarray(imgs[n]).astype(np.float32))
        ws = {(k, s): M[n]["bands"][k]["f" + s] for k in ("hi", "lo") for s in ("l", "r")}
        med = float(np.median(list(ws.values())))
        for (k, s), v in ws.items():
            if abs(v - med) > max(0.22 * med, 4):
                M[n]["bands"][k]["f" + s] = med
        M[n]["f"] = float(np.median([M[n]["bands"][k]["f" + s] for k in ("hi", "lo") for s in ("l", "r")]))
    groups = {}
    for n in names:
        groups.setdefault(re.match(r"pt-\d+", n).group(0), []).append(n)
    for ns in groups.values():
        if len(ns) < 3:
            continue
        rel = {n: M[n]["f"] / M[n]["W"] for n in ns}
        med = float(np.median(list(rel.values())))
        for n in ns:
            if abs(rel[n] - med) > 0.34 * med:
                f = med * M[n]["W"]
                for k in ("hi", "lo"):
                    M[n]["bands"][k]["fl"] = M[n]["bands"][k]["fr"] = f
                M[n]["f"] = f
    table = {}
    for n in names:
        im, m = imgs[n], M[n]
        q = leaf_quad(m, Ls[n])
        wt = ((q[1][0] - q[0][0]) + (q[2][0] - q[3][0])) / 2
        ht = ((q[3][1] - q[0][1]) + (q[2][1] - q[1][1])) / 2
        # warp from the photograph enlarged twice, so the one resample is from finer pixels
        big = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
        leaf = big.transform((LEAF_W, LEAF_H), Image.PERSPECTIVE, persp([[x * 2, y * 2] for x, y in q], LEAF_W, LEAF_H), resample=Image.BICUBIC)
        k = LEAF_H / ht
        leaf = leaf.filter(ImageFilter.UnsharpMask(radius=1.2 if k < 3 else 2.2, percent=65 if k < 3 else 80, threshold=2))
        rgba = leaf.convert("RGBA")
        rgba.save(os.path.join(dst, n + ".webp"), "WEBP", quality=88, method=6)
        rgba.resize((THUMB_W, THUMB_H), Image.LANCZOS).save(os.path.join(dst, "t", n + ".webp"), "WEBP", quality=84, method=6)
        a = np.asarray(leaf).astype(np.float32)
        # the leaf's edge colour: the flat face of its outer stiles, left and right (just inside the bevel at the very
        # edge, which the photograph shades), above and below the handle — what the door's own edges are made of
        rows = np.r_[int(LEAF_H * 0.06):int(LEAF_H * 0.34), int(LEAF_H * 0.62):int(LEAF_H * 0.94)]
        b0, b1 = int(LEAF_W * 0.025), int(LEAF_W * 0.06)
        edge = np.median(np.concatenate([a[rows, b0:b1].reshape(-1, 3), a[rows, LEAF_W - b1:LEAF_W - b0].reshape(-1, 3)]), axis=0)
        # the frame: the middle of its face, both sides, along the door
        P = np.asarray(im).astype(np.float32)
        hi = m["bands"]["hi"]; f = m["f"]
        ys = slice(int(m["y0"] + m["H"] * 0.2), int(m["y0"] + m["H"] * 0.8))
        xl = slice(int(hi["x0"] + f * 0.25), int(hi["x0"] + f * 0.55))
        xr = slice(int(hi["x1"] - f * 0.55), int(hi["x1"] - f * 0.25))
        frame = np.median(np.concatenate([P[ys, xl].reshape(-1, 3), P[ys, xr].reshape(-1, 3)]), axis=0)
        table[n] = {"edge": hexof(edge), "frame": hexof(frame), "aspect": round(wt / ht, 3), "px": round(ht)}
        print(f"{n:30s} leaf {wt:6.1f} x {ht:6.1f} px (x{k:.2f})  aspect {wt / ht:.3f}  edge {hexof(edge)}  frame {hexof(frame)}")
    json.dump(table, open(os.path.join(dst, "leaf.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
