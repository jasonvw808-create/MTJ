"""The eleven pressed stainless steel sinks (LUCKY PRO and wellup), rebuilt as one pressed sheet: the
top of each sink is a single height field — rim band, channel, deck, drainboard relief and bowls —
over the outline, with the turned-down edge lofted round it. Measurements: steel_data.STEEL."""
import math
import numpy as np
import bpy
from . import geo, mats
from .steel_data import STEEL, P

M = 0.001


def _rect_m(rect):
    x0, x1, z0, z1 = rect
    return x0 * M, x1 * M, -z1 * M, -z0 * M


def _radii(r):
    """site radii [x0z0, x1z0, x1z1, x0z1] = [back-left, back-right, front-right, front-left]"""
    if isinstance(r, (list, tuple)):
        return [v * M for v in r]
    return [r * M] * 4


def sd_rrect4(X, Y, x0, x1, y0, y1, r4):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
    bl, br, fr, fl = r4
    r = np.where(X < cx, np.where(Y > cy, bl, fl), np.where(Y > cy, br, fr))
    r = np.minimum(r, min(hx, hy))
    qx = np.abs(X - cx) - (hx - r)
    qy = np.abs(Y - cy) - (hy - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def _poly_pts(poly, r):
    pts = [(x * M, -z * M) for x, z in poly]
    rad = [v * M for v in r] if isinstance(r, (list, tuple)) else [r * M] * len(pts)
    return geo.rpoly(pts, rad, n_corner=8, n_side=2)


def _blade_sd(X, Y, b):
    p0 = np.array([b["p0"][0], -b["p0"][1]]) * M
    p1 = np.array([b["p1"][0], -b["p1"][1]]) * M
    p2 = np.array([b["p2"][0], -b["p2"][1]]) * M
    n = 24
    ts = np.linspace(0, 1, n)
    C = [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2 for t in ts]
    Rr = [(b["w0"] + (b["w2"] - b["w0"]) * t ** b["k"] + b.get("bulge", 0) * math.sin(math.pi * t)) / 2 * M for t in ts]
    d = np.full(X.shape, np.inf)
    for i in range(n - 1):
        a, c = C[i], C[i + 1]
        e = c - a
        L2 = float(e @ e) + 1e-12
        t = np.clip(((X - a[0]) * e[0] + (Y - a[1]) * e[1]) / L2, 0, 1)
        px, py = a[0] + e[0] * t, a[1] + e[1] * t
        rr = Rr[i] + (Rr[i + 1] - Rr[i]) * t
        d = np.minimum(d, np.hypot(X - px, Y - py) - rr)
    return d


def shape_sd(X, Y, shape):
    if "rect" in shape:
        x0, x1, y0, y1 = _rect_m(shape["rect"])
        return sd_rrect4(X, Y, x0, x1, y0, y1, _radii(shape.get("r", 0)))
    if "poly" in shape or "cpoly" in shape:
        return geo.sd_poly(X, Y, _poly_pts(shape.get("poly") or shape.get("cpoly"), shape.get("r", 0)))
    if "stadium" in shape:
        x0, x1, zc, w = shape["stadium"]
        y = -zc * M
        r = w / 2 * M
        a, b = x0 * M + r, x1 * M - r
        px = np.clip(X, a, b)
        return np.hypot(X - px, Y - y) - r
    if "blade" in shape:
        return _blade_sd(X, Y, shape["blade"])
    raise ValueError(shape)


def _bbox(shape, pad=0.01):
    if "rect" in shape:
        x0, x1, y0, y1 = _rect_m(shape["rect"])
    elif "poly" in shape or "cpoly" in shape:
        pts = shape.get("poly") or shape.get("cpoly")
        xs = [p[0] * M for p in pts]
        ys = [-p[1] * M for p in pts]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    elif "stadium" in shape:
        a, b, zc, w = shape["stadium"]
        x0, x1, y0, y1 = a * M, b * M, -zc * M - w * M, -zc * M + w * M
    else:
        bl = shape["blade"]
        xs = [bl[k][0] * M for k in ("p0", "p1", "p2")]
        ys = [-bl[k][1] * M for k in ("p0", "p1", "p2")]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        pad += 0.012
    return x0 - pad, x1 + pad, y0 - pad, y1 + pad


def bowl_profile(S, Dp, lip, fR):
    """(h, v): h inward from the bowl's top outline, v the drop below the deck."""
    pts = [(-0.08, 0.0), (0.0, 0.0), (S, -Dp), (S + 0.6, -Dp)]
    curve = geo.rpoly(pts, [0, lip, fR, 0], n_corner=24, n_side=12)
    # rpoly closes the loop; keep the open run from the first point to the last
    xs = np.array([p[0] for p in curve])
    ys = np.array([p[1] for p in curve])
    i_end = int(np.argmax(xs))
    xs, ys = xs[:i_end + 1], ys[:i_end + 1]
    order = np.argsort(xs)
    xs, ys = xs[order], ys[order]
    keep = np.concatenate([[True], np.diff(xs) > 1e-7])
    return xs[keep], ys[keep]


def _bowl_shapes(b):
    """(top sd fn, floor sd fn) for a bowl dict."""
    sh = b["shape"]
    run = b["run"] * M
    if "cpoly" in sh:
        top = _poly_pts(sh["cpoly"], sh["r"])
        # floor: the polygon pulled in by the run, with its own radii
        raw = np.array([(x * M, -z * M) for x, z in sh["cpoly"]])
        c = raw.mean(0)
        inner = []
        n = len(raw)
        for i in range(n):
            p0, p1, p2 = raw[i - 1], raw[i], raw[(i + 1) % n]
            d0 = (p0 - p1) / np.linalg.norm(p0 - p1)
            d2 = (p2 - p1) / np.linalg.norm(p2 - p1)
            bis = d0 + d2
            bis = bis / np.linalg.norm(bis)
            s = math.sin(math.acos(max(-1, min(1, float(d0 @ d2)))) / 2)
            q = p1 + bis * run / max(s, 0.2)
            if np.dot(q - p1, c - p1) < 0:
                q = p1 - bis * run / max(s, 0.2)
            inner.append(q)
        flo = geo.rpoly([tuple(p) for p in inner], [v * M for v in sh["rBottom"]], n_corner=8, n_side=2)
        return (lambda X, Y: geo.sd_poly(X, Y, top)), (lambda X, Y: geo.sd_poly(X, Y, flo)), top
    x0, x1, y0, y1 = _rect_m(sh["rect"])
    r = sh["r"] * M
    rb = b["rBottom"] * M
    top_pts = geo.rrect(x0, x1, y0, y1, r)
    return (lambda X, Y: geo.sd_rrect(X, Y, x0, x1, y0, y1, r)), \
           (lambda X, Y: geo.sd_rrect(X, Y, x0 + run, x1 - run, y0 + run, y1 - run, rb)), top_pts


def _apply_bowl(Z, X, Y, b, level):
    top_sd, floor_sd, top_pts = _bowl_shapes(b)
    xs = [p[0] for p in top_pts]
    ys = [p[1] for p in top_pts]
    pad = b["lip"] * M + 0.004
    sel = (X > min(xs) - pad) & (X < max(xs) + pad) & (Y > min(ys) - pad) & (Y < max(ys) + pad)
    dr = b["drain"]
    if not sel.any():
        return (dr["x"] * M, -dr["z"] * M, dr["d"] / 2 * M, level - b["depth"] * M - b["fall"] * M - dr.get("lip", 4) * M, dr.get("type", "hole"))
    Xs, Ys = X[sel], Y[sel]
    a = top_sd(Xs, Ys)
    bb = floor_sd(Xs, Ys)
    S = b["run"] * M
    Dp = b["depth"] * M
    hx, hv = bowl_profile(S, Dp, b["lip"] * M, b["floorR"] * M)
    with np.errstate(divide='ignore', invalid='ignore'):
        u = np.where(bb - a > 1e-9, -a / (bb - a), 1.0)
    h = np.where(a >= 0, -a, np.where(bb > 0, S * np.clip(u, 0, 1), S - bb))
    v = np.interp(h, hx, hv, left=0.0, right=-Dp)
    z = level + v
    # the floor dished towards the drain
    dr = b["drain"]
    dx, dy = dr["x"] * M, -dr["z"] * M
    dist = np.hypot(Xs - dx, Ys - dy)
    inside = geo.smoothstep(0.0, 0.03, -bb)
    Rmax = max(0.05, float(np.max(np.where(bb < 0, dist, 0))))
    z -= b["fall"] * M * inside * (1 - np.clip(dist / Rmax, 0, 1)) ** 1.3
    # the waste hole's rounded rim
    rh = dr["d"] / 2 * M
    lipd = dr.get("lip", 4) * M
    z -= lipd * (1 - np.clip((dist - rh) / lipd, 0, 1)) ** 2 * (dist < rh + lipd)
    Z[sel] = np.minimum(Z[sel], z)
    return (dx, dy, rh, level - Dp - b["fall"] * M - lipd, dr.get("type", "hole"))


def _apply_regions(Z, X, Y, regions, level, drains):
    for reg in regions:
        sh = reg["shape"]
        x0, x1, y0, y1 = _bbox(sh, pad=reg.get("e", 3) * M + 0.002)
        sel = (X > x0) & (X < x1) & (Y > y0) & (Y < y1)
        if not sel.any():
            continue
        Xs, Ys = X[sel], Y[sel]
        sd = shape_sd(Xs, Ys, sh)
        e = max(reg.get("e", 3), 0.6) * M
        f = geo.smoothstep(0.0, e, -sd)
        Z[sel] += reg["h"] * M * f
        lev = level + reg["h"] * M
        if reg.get("children"):
            _apply_regions(Z, X, Y, reg["children"], lev, drains)
        for b in reg.get("bowls", []):
            drains.append(_apply_bowl(Z, X, Y, b, lev))


def build(model, col=None, res=0.0008):
    d = STEEL[model]
    W, D = d["size"][0] * M, d["size"][1] * M
    cr = d["cornerR"] * M
    band, channel = d["rim"]["band"] * M, d["rim"]["channel"] * M
    cd, dd = P["channelDepth"] * M, P["deckDrop"] * M
    edgeR = P["edgeR"] * M
    skirt = P["skirt"] * M
    mat = mats.steel(d["finish"])
    drains = []

    def hfun(X, Y):
        so = geo.sd_rrect(X, Y, -W / 2, W / 2, -D / 2, D / 2, cr)
        s = -so
        z = np.zeros_like(X)
        c0, c1, c2 = band, band + channel / 2, band + channel
        z = np.where(s > c0, -cd * geo.smoothstep(c0, c1, s), z)
        z = np.where(s > c1, -cd + (cd - dd) * geo.smoothstep(c1, c2, s), z)
        z = np.where(s > c2, -dd, z)
        _apply_regions(z, X, Y, d["features"], -dd, drains)
        for b in d["bowls"]:
            drains.append(_apply_bowl(z, X, Y, b, -dd))
        hfun.drains = drains
        return z

    holes = []

    def mask(X, Y):
        so = geo.sd_rrect(X, Y, -W / 2, W / 2, -D / 2, D / 2, cr)
        keep = so < -(edgeR + 0.0009)
        for (dx, dy, rh, zb, kind) in drains:
            keep &= np.hypot(X - dx, Y - dy) > rh * 0.92
        return keep

    # heights first (fills `drains`), then the mask that needs them
    top = geo.heightfield(-W / 2, W / 2, -D / 2, D / 2, res, hfun, name=model + "_top", mat=mat, collection=col, mask=mask)
    objs = [top]
    # the turned-down edge: flat for 2 mm (over the field's edge), the round, then down the skirt
    rings = []
    def ring(inset, z):
        rr = max(0.0006, cr - inset)
        return [(x, y, z) for x, y in geo.rrect(-W / 2 + inset, W / 2 - inset, -D / 2 + inset, D / 2 - inset, rr, n_corner=12, n_side=(40, 20))]
    rings.append(ring(edgeR + 0.002, 0.00003))
    for k in range(9):
        th = (math.pi / 2) * k / 8
        rings.append(ring(edgeR - edgeR * math.sin(th), -edgeR + edgeR * math.cos(th) + 0.00003))
    rings.append(ring(0.0, -skirt))
    objs.append(geo.loft(rings, name=model + "_edge", mat=mat, collection=col, smooth_angle=60, flip=True))
    # wastes
    for i, (dx, dy, rh, zb, kind) in enumerate(hfun.drains if hasattr(hfun, "drains") else drains):
        objs += waste(f"{model}_waste{i}", dx, dy, zb, rh, kind, col)
    for o in objs:
        o["sink"] = model
    cut = [geo.rrect(-W / 2 + 0.025, W / 2 - 0.025, -D / 2 + 0.025, D / 2 - 0.025, 0.01)]
    return dict(objects=objs, cutout=cut, mount="inset", flange=skirt, outline=geo.rrect(-W / 2, W / 2, -D / 2, D / 2, cr),
                size=(W, D), depth=d["height"] * M, rim_above=skirt)


def waste(name, x, y, z_hole, r, kind, col):
    """The waste in each bowl: a steel flange round the hole and a basket below; a plain cap for 'cap'."""
    objs = []
    steel = mats.metal("steel")
    dark = mats.rubber_dark()
    zt = z_hole + 0.004
    if kind == "popup":
        objs.append(geo.lathe([(0.0, 0.006), (r * 0.8, 0.0055), (r * 0.98, 0.003), (r * 1.02, 0.0)], n=48, name=name, mat=mats.metal("chrome"), collection=col, cx=x, cy=y, z=zt - 0.004))
        return objs
    # flange
    objs.append(geo.lathe([(r * 0.82, 0.0), (r * 0.82, 0.0022), (r * 1.08, 0.0022), (r * 1.14, 0.0)], n=64, name=name + "_flange", mat=steel, collection=col, cx=x, cy=y, z=zt - 0.0035))
    # the basket: a dark perforated cup
    objs.append(geo.lathe([(r * 0.82, 0.0), (r * 0.78, -0.03), (r * 0.6, -0.06), (0.0, -0.062)], n=48, name=name + "_basket", mat=mats.perforated(), collection=col, cx=x, cy=y, z=zt - 0.0035))
    objs.append(geo.cylinder(x, y, zt - 0.08, zt - 0.062, r * 0.9, 32, name=name + "_dark", mat=dark, collection=col))
    if kind == "cap":
        objs.append(geo.lathe([(0.0, 0.004), (r * 0.7, 0.0035), (r * 0.95, 0.0015), (r * 0.98, 0.0)], n=48, name=name + "_cap", mat=mats.spun_steel(), collection=col, cx=0, cy=0, z=0))
        objs[-1].location = (x, y, zt - 0.0015)
    return objs
