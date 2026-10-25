"""Technical drawings for the catalogue pages, as SVG.

Each drawing is built from the same measurements the 3D models use (render/granite_data.py,
render/steel_data.py): the overall outline at its listed size, the bowls, wastes, tap holes and
drainboard relief as measured from the supplied product photographs. Only the listed overall
dimensions are labelled; everything else is drawn for reference."""
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from render.granite_data import GRANITE  # noqa: E402
from render.steel_data import STEEL, P as PEST  # noqa: E402

INK = "#2b2926"
SOFT = "#8c857c"
FAINT = "#b9b2a8"


def _arc(cx, cy, r, a0, a1, n=8):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def rrect_pts(x0, x1, y0, y1, r):
    """Rounded rectangle in drawing coordinates (y down). r: one radius or
    [top-left, top-right, bottom-right, bottom-left]."""
    if not isinstance(r, (list, tuple)):
        r = [r] * 4
    w, h = x1 - x0, y1 - y0
    r = [max(0.0, min(v, w / 2, h / 2)) for v in r]
    tl, tr, br, bl = r
    pts = []
    pts += _arc(x1 - tr, y0 + tr, tr, -math.pi / 2, 0)
    pts += _arc(x1 - br, y1 - br, br, 0, math.pi / 2)
    pts += _arc(x0 + bl, y1 - bl, bl, math.pi / 2, math.pi)
    pts += _arc(x0 + tl, y0 + tl, tl, math.pi, 1.5 * math.pi)
    return pts


def rpoly_pts(points, radii):
    """Polygon with rounded corners (any orientation)."""
    k = len(points)
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * k
    out = []
    for i in range(k):
        p0, p1, p2 = points[i - 1], points[i], points[(i + 1) % k]
        d0 = (p0[0] - p1[0], p0[1] - p1[1])
        d2 = (p2[0] - p1[0], p2[1] - p1[1])
        l0, l2 = math.hypot(*d0), math.hypot(*d2)
        d0 = (d0[0] / l0, d0[1] / l0)
        d2 = (d2[0] / l2, d2[1] / l2)
        r = radii[i]
        cosang = max(-1, min(1, d0[0] * d2[0] + d0[1] * d2[1]))
        ang = math.acos(cosang)
        if r <= 0 or ang > math.pi - 1e-3:
            out.append(p1)
            continue
        t = min(r / math.tan(ang / 2), 0.49 * l0, 0.49 * l2)
        r = t * math.tan(ang / 2)
        a = (p1[0] + d0[0] * t, p1[1] + d0[1] * t)
        b = (p1[0] + d2[0] * t, p1[1] + d2[1] * t)
        bx, by = d0[0] + d2[0], d0[1] + d2[1]
        bl = math.hypot(bx, by)
        c = (p1[0] + bx / bl * r / math.sin(ang / 2), p1[1] + by / bl * r / math.sin(ang / 2))
        a0 = math.atan2(a[1] - c[1], a[0] - c[0])
        a1 = math.atan2(b[1] - c[1], b[0] - c[0])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        out += [(c[0] + r * math.cos(a0 + da * j / 8), c[1] + r * math.sin(a0 + da * j / 8)) for j in range(9)]
    return out


class Drawing:
    """Collects shapes in product millimetres and writes them out scaled into a box (page mm)."""

    def __init__(self):
        self.items = []  # (kind, data, style)

    def poly(self, pts, cls="line"):
        self.items.append(("poly", pts, cls))

    def circle(self, x, y, r, cls="line"):
        self.items.append(("circle", (x, y, r), cls))

    def line(self, a, b, cls="line"):
        self.items.append(("seg", (a, b), cls))


STYLE = {
    "outline": f'fill="none" stroke="{INK}" stroke-width="0.32"',
    "line": f'fill="none" stroke="{INK}" stroke-width="0.2"',
    "soft": f'fill="none" stroke="{SOFT}" stroke-width="0.16"',
    "faint": f'fill="none" stroke="{FAINT}" stroke-width="0.13" stroke-dasharray="0.8 0.6"',
    "relief": f'fill="none" stroke="{SOFT}" stroke-width="0.12"',
    "glass": f'fill="#d9d4cc" fill-opacity="0.55" stroke="{SOFT}" stroke-width="0.14"',
}


def _fmt(v):
    return f"{v:.2f}".rstrip('0').rstrip('.')


def plan_granite(model):
    g = GRANITE[model]
    W, D = g["size"]
    d = Drawing()
    cr = g["cornerR"]
    if isinstance(cr, (list, tuple)):
        rr = [cr[0], cr[0], cr[1], cr[1]]  # back corners at the top
    else:
        rr = cr
    d.poly(rrect_pts(-W / 2, W / 2, -D / 2, D / 2, rr), "outline")
    L, R, B, F = g["rim"]
    x0, x1 = -W / 2 + L, W / 2 - R
    y0, y1 = -D / 2 + B, D / 2 - F  # y down: back (top) first
    bowls = [(x0, x1)]
    if g["bowls"] == 2:
        h = g["divider"] / 2
        bowls = [(x0, -h), (h, x1)]
    for (a, b) in bowls:
        d.poly(rrect_pts(a, b, y0, y1, g["bowlR"]), "line")
        # the floor's edge, the walls having stepped in (for reference)
        led = g.get("ledge")
        yb = y0 + g["runZ"] + (led["w"] if led else 0)
        d.poly(rrect_pts(a + g["runX"] + 10, b - g["runX"] - 10, yb + 10, y1 - g["runZ"] - 10, max(2, g["bowlR"] - 4)), "faint")
        if led:
            d.line((a, y0 + led["w"]), (b, y0 + led["w"]), "soft")
    for i, (a, b) in enumerate(bowls):
        dr = g["drains"][min(i, len(g["drains"]) - 1)]
        if dr["x"] is None:
            cx, cy = (a + b) / 2, (y0 + y1) / 2 - 96
        else:
            cx, cy = dr["x"], dr["z"]
        d.circle(cx, cy, dr["ring"] / 2, "line")
        d.circle(cx, cy, dr["d"] / 2 * 0.55, "soft")
    for h in g.get("holes", []):
        d.circle(h["x"], h["z"], h["d"] / 2, "line")
    st = g.get("floorStep")
    if st:
        sx, sy, r = st["x"], st["z"], st["r"]
        top = y0 + g["runZ"] + 10 + (g["ledge"]["w"] if g.get("ledge") else 0)
        bot = y1 - g["runZ"] - 10
        pts = [(sx, top), (sx, sy - r)] + _arc(sx, sy, r, -math.pi / 2, -1.5 * math.pi, 16) + [(sx, sy + r), (sx, bot)]
        d.items.append(("open", pts, "soft"))
    return d, (W, D)


def _rect_site(rect):
    x0, x1, z0, z1 = rect
    return x0, x1, z0, z1  # y down = z (back negative is up)


def _site_radii(r):
    # site radii [x0z0, x1z0, x1z1, x0z1] = [back-left, back-right, front-right, front-left] = [tl, tr, br, bl]
    return list(r) if isinstance(r, (list, tuple)) else r


def _shape_pts(shape):
    if "rect" in shape:
        x0, x1, z0, z1 = shape["rect"]
        return rrect_pts(x0, x1, z0, z1, _site_radii(shape.get("r", 0)))
    if "poly" in shape or "cpoly" in shape:
        pts = [tuple(p) for p in (shape.get("poly") or shape.get("cpoly"))]
        return rpoly_pts(pts, shape.get("r", 0))
    if "stadium" in shape:
        x0, x1, zc, w = shape["stadium"]
        r = w / 2
        return _arc(x1 - r, zc, r, -math.pi / 2, math.pi / 2, 8) + _arc(x0 + r, zc, r, math.pi / 2, 1.5 * math.pi, 8)
    if "blade" in shape:
        b = shape["blade"]
        p0, p1, p2 = b["p0"], b["p1"], b["p2"]
        n = 20
        cs, ws = [], []
        for i in range(n + 1):
            t = i / n
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
            cs.append((x, y))
            ws.append((b["w0"] + (b["w2"] - b["w0"]) * t ** b["k"] + b.get("bulge", 0) * math.sin(math.pi * t)) / 2)
        left, right = [], []
        for i in range(n + 1):
            a = cs[max(0, i - 1)]
            c = cs[min(n, i + 1)]
            tx, ty = c[0] - a[0], c[1] - a[1]
            L = math.hypot(tx, ty) or 1
            nx, ny = -ty / L, tx / L
            left.append((cs[i][0] + nx * ws[i], cs[i][1] + ny * ws[i]))
            right.append((cs[i][0] - nx * ws[i], cs[i][1] - ny * ws[i]))
        return left + right[::-1]
    return []


def _features(d, feats):
    for f in feats:
        pts = _shape_pts(f["shape"])
        if pts:
            d.poly(pts, "relief")
        _features(d, f.get("children", []))
        for b in f.get("bowls", []):
            _pbowl(d, b)


def _pbowl(d, b):
    sh = b["shape"]
    if "cpoly" in sh:
        d.poly(rpoly_pts([tuple(p) for p in sh["cpoly"]], sh["r"]), "line")
    else:
        x0, x1, z0, z1 = sh["rect"]
        d.poly(rrect_pts(x0, x1, z0, z1, sh["r"]), "line")
        run = b.get("run", 38)
        d.poly(rrect_pts(x0 + run, x1 - run, z0 + run, z1 - run, b.get("rBottom", 20)), "faint")
    dr = b["drain"]
    d.circle(dr["x"], dr["z"], dr["d"] / 2, "line")


def plan_steel(model):
    s = STEEL[model]
    W, D = s["size"]
    d = Drawing()
    d.poly(rrect_pts(-W / 2, W / 2, -D / 2, D / 2, s["cornerR"]), "outline")
    if s["family"] == "pressed":
        band = s["rim"]["band"]
        d.poly(rrect_pts(-W / 2 + band, W / 2 - band, -D / 2 + band, D / 2 - band, max(2, s["cornerR"] - 4)), "soft")
        _features(d, s["features"])
        for b in s["bowls"]:
            _pbowl(d, b)
        return d, (W, D)
    # hand made
    if s.get("top") == "glass":
        op = s["opening"]
        x0, x1, z0, z1 = op["rect"]
        d.poly(rrect_pts(x0, x1, z0, z1, op["r"]), "soft")
        b = op["bowl"]
        bx0, bx1, bz0, bz1 = b["shape"]["rect"]
        d.poly(rrect_pts(bx0, bx1, bz0, bz1, b["shape"]["r"]), "line")
        dr = b["drain"]
        d.circle(dr["x"], dr["z"], dr["d"] / 2, "line")
        for gr in s["grooves"]:
            d.line((gr["x0"], gr["z"]), (gr["x1"], gr["z"]), "relief")
        for f in s["fittings"]:
            if f["kind"] == "tapring":
                d.circle(f["x"], f["z"], f["d"] / 2, "line")
                d.circle(f["x"], f["z"], f["d"] / 2 * 0.6, "soft")
        return d, (W, D)
    if s.get("recesses"):
        for rc in s["recesses"]:
            x0, x1, z0, z1 = rc["rect"]
            d.poly(rrect_pts(x0, x1, z0, z1, rc["r"]), "line")
        for f in s["fittings"]:
            if f["kind"] == "pane":
                d.poly(rrect_pts(f["x0"], f["x1"], f["z0"], f["z1"], 4), "glass")
        return d, (W, D)
    for b in s["bowls"]:
        x0, x1, z0, z1 = b["shape"]["rect"]
        d.poly(rrect_pts(x0, x1, z0, z1, b["shape"]["r"]), "line")
        if b.get("ledges"):
            w = b["ledges"]["back"]["w"]
            d.line((x0, z0 + w), (x1, z0 + w), "soft")
            d.line((x0, z1 - w), (x1, z1 - w), "soft")
        dr = b["drain"]
        d.circle(dr["x"], dr["z"], dr["d"] / 2, "line")
    return d, (W, D)


def elevation_steel(model):
    """The front view: deck or rim, and the bowls below it down to the listed height."""
    s = STEEL[model]
    W, D = s["size"]
    Hh = s["height"]
    d = Drawing()
    if s["family"] == "pressed":
        skirt = PEST["skirt"]
        d.poly([(-W / 2, 0), (W / 2, 0), (W / 2, skirt), (-W / 2, skirt)], "outline")
        for b in s["bowls"]:
            sh = b["shape"]
            if "cpoly" in sh:
                xs = [p[0] for p in sh["cpoly"]]
                x0, x1 = min(xs), max(xs)
            else:
                x0, x1 = sh["rect"][0], sh["rect"][1]
            run = b.get("run", 38)
            rb = 26
            pts = [(x0, skirt), (x1, skirt)] + _arc(x1 - run - rb + 6, Hh - rb, rb, 0, math.pi / 2, 8)[::-1][::-1]
            body = [(x0, skirt), (x1, skirt), (x1 - run * 0.55, Hh - rb * 0.6)] + _arc(x1 - run - rb * 0.3, Hh - rb, rb, 0.25, math.pi / 2, 8) \
                + _arc(x0 + run + rb * 0.3, Hh - rb, rb, math.pi / 2, math.pi - 0.25, 8) + [(x0 + run * 0.55, Hh - rb * 0.6)]
            d.poly(body, "line")
        return d, (W, Hh)
    plate = 3
    d.poly([(-W / 2, 0), (W / 2, 0), (W / 2, plate), (-W / 2, plate)], "outline")
    bowls = s["bowls"]
    if s.get("top") == "glass":
        bowls = [s["opening"]["bowl"]]
    if s.get("recesses"):
        bowls = [dict(shape=dict(rect=rc["bowl"]["rect"], r=rc["bowl"]["r"])) for rc in s["recesses"]]
    for b in bowls:
        x0, x1 = b["shape"]["rect"][0], b["shape"]["rect"][1]
        r = 8
        body = [(x0, plate), (x1, plate)] + _arc(x1 - r, Hh - r, r, 0, math.pi / 2, 6) + _arc(x0 + r, Hh - r, r, math.pi / 2, math.pi, 6)
        d.poly(body, "line" if not s.get("recesses") else "faint")
    return d, (W, Hh)


def _dim_h(x0, x1, y, label, s, ox, oy, tick=1.1, text_dy=-1.2):
    """A horizontal dimension line between x0 and x1 (product mm) at page y (mm)."""
    X0, X1 = ox + x0 * s, ox + x1 * s
    out = [f'<line x1="{_fmt(X0)}" y1="{_fmt(y)}" x2="{_fmt(X1)}" y2="{_fmt(y)}" stroke="{SOFT}" stroke-width="0.14"/>']
    for X in (X0, X1):
        out.append(f'<line x1="{_fmt(X - tick * 0.7)}" y1="{_fmt(y + tick * 0.7)}" x2="{_fmt(X + tick * 0.7)}" y2="{_fmt(y - tick * 0.7)}" stroke="{INK}" stroke-width="0.22"/>')
        out.append(f'<line x1="{_fmt(X)}" y1="{_fmt(y - 1.6)}" x2="{_fmt(X)}" y2="{_fmt(y + 1.6)}" stroke="{SOFT}" stroke-width="0.12"/>')
    out.append(f'<text x="{_fmt((X0 + X1) / 2)}" y="{_fmt(y + text_dy)}" text-anchor="middle" class="dim">{label}</text>')
    return out


def _dim_v(y0, y1, x, label, s, ox, oy, tick=1.1):
    Y0, Y1 = oy + y0 * s, oy + y1 * s
    out = [f'<line x1="{_fmt(x)}" y1="{_fmt(Y0)}" x2="{_fmt(x)}" y2="{_fmt(Y1)}" stroke="{SOFT}" stroke-width="0.14"/>']
    for Y in (Y0, Y1):
        out.append(f'<line x1="{_fmt(x - tick * 0.7)}" y1="{_fmt(Y + tick * 0.7)}" x2="{_fmt(x + tick * 0.7)}" y2="{_fmt(Y - tick * 0.7)}" stroke="{INK}" stroke-width="0.22"/>')
        out.append(f'<line x1="{_fmt(x - 1.6)}" y1="{_fmt(Y)}" x2="{_fmt(x + 1.6)}" y2="{_fmt(Y)}" stroke="{SOFT}" stroke-width="0.12"/>')
    cy = (Y0 + Y1) / 2
    out.append(f'<text x="{_fmt(x + 1.9)}" y="{_fmt(cy + 0.9)}" text-anchor="start" class="dim">{label}</text>')
    return out


def _emit(d, s, ox, oy):
    out = []
    for kind, data, cls in d.items:
        st = STYLE[cls]
        if kind == "poly":
            pts = " ".join(f"{_fmt(ox + x * s)},{_fmt(oy + y * s)}" for x, y in data)
            out.append(f'<polygon points="{pts}" {st}/>')
        elif kind == "open":
            pts = " ".join(f"{_fmt(ox + x * s)},{_fmt(oy + y * s)}" for x, y in data)
            out.append(f'<polyline points="{pts}" {st}/>')
        elif kind == "circle":
            x, y, r = data
            out.append(f'<circle cx="{_fmt(ox + x * s)}" cy="{_fmt(oy + y * s)}" r="{_fmt(r * s)}" {st}/>')
        elif kind == "seg":
            (a, b) = data
            out.append(f'<line x1="{_fmt(ox + a[0] * s)}" y1="{_fmt(oy + a[1] * s)}" x2="{_fmt(ox + b[0] * s)}" y2="{_fmt(oy + b[1] * s)}" {st}/>')
    return out


def svg(kind, model, box_w=86.0, box_h=72.0, width_label=None, max_scale=None):
    """The model's drawing fitted into box_w x box_h (page mm). kind: 'granite' or 'steel'.
    Returns (svg string, scale) — scale as page mm per product mm."""
    if kind == "granite":
        plan, (W, D) = plan_granite(model)
        elev, Hh = None, None
    else:
        plan, (W, D) = plan_steel(model)
        elev, (_, Hh) = elevation_steel(model)
    pad_l, pad_r, pad_t = 1.0, 11.0, 6.5
    gap = 9.0
    avail_w = box_w - pad_l - pad_r
    avail_h = box_h - pad_t - (gap + 2.0 if elev else 2.0)
    total_h = D + (Hh if elev else 0)
    s = min(avail_w / W, avail_h / total_h)
    if max_scale:
        s = min(s, max_scale)
    ox = pad_l + W / 2 * s + (avail_w - W * s) / 2 * 0.0
    oy = pad_t + D / 2 * s
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_fmt(box_w)} {_fmt(box_h)}" width="{_fmt(box_w)}mm" height="{_fmt(box_h)}mm" class="drawing">']
    out += _emit(plan, s, ox, oy)
    wl = width_label if width_label is not None else str(W)
    out += _dim_h(-W / 2, W / 2, pad_t - 3.0, wl, s, ox, oy)
    out += _dim_v(-D / 2, D / 2, ox + W / 2 * s + 3.2, str(D), s, ox, oy)
    if elev:
        ey = oy + D / 2 * s + gap
        out += _emit(elev, s, ox, ey)
        out += _dim_v(0, Hh, ox + W / 2 * s + 3.2, str(Hh), s, ox, ey)
    out.append('</svg>')
    return "\n".join(out), s


if __name__ == "__main__":
    os.makedirs(sys.argv[1], exist_ok=True)
    for m in GRANITE:
        open(os.path.join(sys.argv[1], m.replace(" ", "_") + ".svg"), "w").write(svg("granite", m)[0])
    for m in STEEL:
        open(os.path.join(sys.argv[1], m.replace(" ", "_") + ".svg"), "w").write(svg("steel", m)[0])
