"""The six granite composite sinks, rebuilt from the measurements the shop's site
took from the supplied product photographs (index.html: SINK_3D, COUNTER_3D) and the
listed sizes. Millimetres in the tables; metres in the scene. x across, y front->back
(the site's z is front->back with the back negative, so y = -z).

What the photographs cannot show (bowl depth, rim thickness, wall-to-floor radius,
the round on the bowls' top edge) uses the same typical values as the site."""
import math
import bpy
from . import geo
from . import mats

from .granite_data import EST, GRANITE

M = 0.001


def _corner_list(cr):
    # site: number, or [back, front] -> rrect order [front-left, front-right, back-right, back-left]
    if isinstance(cr, (list, tuple)):
        b, f = cr
        return [f * M, f * M, b * M, b * M]
    return cr * M


def outline(model):
    g = GRANITE[model]
    W, D = g["size"]
    return geo.rrect(-W / 2 * M, W / 2 * M, -D / 2 * M, D / 2 * M, _corner_list(g["cornerR"]), n_corner=10, n_side=(12, 8))


def bowl_rects(model):
    """Each bowl's opening (top of its walls): (x0, x1, y0, y1) in metres."""
    g = GRANITE[model]
    W, D = g["size"]
    L, R, B, F = g["rim"]
    x0, x1 = -W / 2 + L, W / 2 - R
    y0, y1 = -D / 2 + F, D / 2 - B  # front edge (y0) is the front rim; back edge (y1) inside the back rim
    if g["bowls"] == 2:
        h = g["divider"] / 2
        return [(x0 * M, -h * M, y0 * M, y1 * M), (h * M, x1 * M, y0 * M, y1 * M)]
    return [(x0 * M, x1 * M, y0 * M, y1 * M)]


def cutout(model, reveal=3.0):
    """The countertop's cut-out, sink-local. Undermount: each bowl's opening plus a reveal (one cut-out
    spanning both bowls of a double sink, so the divider shows). Top-mount: inside the rim."""
    g = GRANITE[model]
    if g["mount"] == "under":
        rs = bowl_rects(model)
        x0 = min(r[0] for r in rs) - reveal * M
        x1 = max(r[1] for r in rs) + reveal * M
        y0 = rs[0][2] - reveal * M
        y1 = rs[0][3] + reveal * M
        return [geo.rrect(x0, x1, y0, y1, (g["bowlR"] + reveal) * M)]
    W, D = g["size"]
    m = 16 * M
    return [geo.rrect(-W / 2 * M + m, W / 2 * M - m, -D / 2 * M + m, D / 2 * M - m, 6 * M)]


def _bowl(name, rect, g, mat, col, ledge=None):
    """Loft one bowl: the round on the top edge, drafted walls (a ledge on the back if any), the floor
    fillet. Returns (object, floor ring rect) — the floor itself is filled separately."""
    x0, x1, y0, y1 = rect
    D = EST["depth"] * M
    lip = EST["lip"] * M
    F = EST["floorR"] * M
    rx, ry = g["runX"] * M, g["runZ"] * M
    r = g["bowlR"] * M
    nc, ns = 8, (16, 10)
    rings = []

    def ring(ix, iy_f, iy_b, z, rr):
        pts = geo.rrect(x0 + ix, x1 - ix, y0 + iy_f, y1 - iy_b, max(0.0008, rr), n_corner=nc, n_side=ns)
        return [(px, py, z) for (px, py) in pts]

    # lip: from the rim top (offset outward by lip) down to the wall
    for k in range(7):
        th = (math.pi / 2) * k / 6
        off = lip - lip * math.sin(th)
        z = -lip + lip * math.cos(th)
        rings.append(ring(-off, -off, -off, z, r + off))
    led = ledge or None
    # walls, drafted: inset grows linearly with depth
    zs = []
    z_top, z_bot = -lip, -(D - F)
    n_wall = 6
    for k in range(1, n_wall + 1):
        zs.append(z_top + (z_bot - z_top) * k / n_wall)
    if led:
        zd = -led["drop"] * M
        w = led["w"] * M
        # down to the ledge, across it (back side only), then on down
        pre = [z for z in zs if z > zd]
        post = [z for z in zs if z < zd]
        for z in pre:
            t = -z / D
            rings.append(ring(rx * t, ry * t, ry * t, z, r))
        t = -zd / D
        rings.append(ring(rx * t, ry * t, ry * t, zd, r))
        rings.append(ring(rx * t, ry * t, ry * t + w, zd - 0.0002, r))
        for z in post:
            t = -z / D
            rings.append(ring(rx * t, ry * t, ry * t + w, z, r))
        back_extra = w
    else:
        for z in zs:
            t = -z / D
            rings.append(ring(rx * t, ry * t, ry * t, z, r))
        back_extra = 0.0
    # floor fillet
    t = (D - F) / D
    bx, by = rx * t, ry * t
    for k in range(1, 7):
        th = (math.pi / 2) * k / 6
        add = F - F * math.cos(th)
        z = -(D - F) - F * math.sin(th)
        rings.append(ring(bx + add, by + add, by + add + back_extra, z, max(0.002, r - add * 0.4)))
    ob = geo.loft(rings, name=name, mat=mat, collection=col, smooth_angle=60)
    fl = (x0 + bx + F, x1 - bx - F, y0 + by + F, y1 - by - F - back_extra, max(0.002, r - F * 0.4))
    return ob, fl, rings[-1]


def build(model, colour, col=None, fittings_colour=None):
    """Build the sink, top of its rim at z = 0, centred on the origin. Returns a dict with the
    objects, the countertop cut-out (sink-local) and how it is mounted."""
    g = GRANITE[model]
    gm = mats.granite_composite(colour)
    objs = []
    W, D = g["size"]
    out = outline(model)
    rects = bowl_rects(model)
    lip = EST["lip"] * M
    flange = EST["flange"] * M
    # each bowl
    floors = []
    for i, rc in enumerate(rects):
        ob, fl, last = _bowl(f"{model}_bowl{i}", rc, g, gm, col, ledge=g.get("ledge"))
        objs.append(ob)
        floors.append((fl, last))
    # the rim's top: the outline less each bowl's opening (offset by the lip)
    holes = []
    for rc in rects:
        x0, x1, y0, y1 = rc
        holes.append(geo.rrect(x0 - lip, x1 + lip, y0 - lip, y1 + lip, g["bowlR"] * M + lip, n_corner=8, n_side=(16, 10)))
    tap_holes = []
    for h in g.get("holes", []):
        tap_holes.append(geo.circle(h["x"] * M, -h["z"] * M, h["d"] / 2 * M, 32))
    edgeR = g.get("edgeR", 1.0) * M
    crs = _corner_list(g["cornerR"])
    crs = crs if isinstance(crs, list) else [crs] * 4
    deck_out = geo.rrect(-W / 2 * M + edgeR, W / 2 * M - edgeR, -D / 2 * M + edgeR, D / 2 * M - edgeR,
                         [max(0.0008, c - edgeR) for c in crs], n_corner=10, n_side=(14, 8))
    objs.append(geo.fill_with_holes(deck_out, holes + tap_holes, z=0.0, name=f"{model}_deck", mat=gm, collection=col))
    # the outer edge: a round, then straight down the rim's thickness
    rings = []
    for k in range(7):
        th = (math.pi / 2) * k / 6
        off = edgeR - edgeR * math.sin(th)       # inset from the outline
        z = -edgeR + edgeR * math.cos(th)
        pts = geo.rrect(-W / 2 * M + off, W / 2 * M - off, -D / 2 * M + off, D / 2 * M - off, [max(0.0008, c - off) for c in crs], n_corner=10, n_side=(14, 8))
        rings.append([(x, y, z) for x, y in pts])
    pts = geo.rrect(-W / 2 * M, W / 2 * M, -D / 2 * M, D / 2 * M, crs, n_corner=10, n_side=(14, 8))
    rings.append([(x, y, -flange) for x, y in pts])
    objs.append(geo.loft(rings, name=f"{model}_edge", mat=gm, collection=col, smooth_angle=50, flip=True))
    # tap holes: a short bore
    for h in g.get("holes", []):
        cx, cy, r = h["x"] * M, -h["z"] * M, h["d"] / 2 * M
        objs.append(geo.cylinder(cx, cy, -flange, 0.0, r, 32, name=f"{model}_taphole", mat=gm, collection=col, cap_top=False, cap_bottom=True))
    # floors, with the drains
    Dz = EST["depth"] * M
    drains = g["drains"]
    for i, (fl, last) in enumerate(floors):
        dr = drains[min(i, len(drains) - 1)]
        x0, x1, y0, y1 = rects[i]
        dx = (x0 + x1) / 2 if dr["x"] is None else dr["x"] * M
        dy = (y0 + y1) / 2 - (dr["z"] * M) if dr["x"] is None else -dr["z"] * M
        if dr["x"] is None:
            # GDU 8145: centred side to side; 96 mm behind the middle of the bowl
            dy = (y0 + y1) / 2 + 0.096
        ring_r = dr["ring"] / 2 * M
        floor_poly = [(p[0], p[1]) for p in last]
        fz = -Dz
        step = g.get("floorStep")
        if step:
            # GST 7546: the floor in two levels; the drain's side (right of x = 192 and round the drain) 2 mm lower
            objs.append(geo.fill_with_holes(floor_poly, [geo.circle(dx, dy, ring_r, 48)], z=fz, name=f"{model}_floor", mat=gm, collection=col))
            objs += _raised_floor_left(model, floor_poly, step, gm, col, fz)
        else:
            objs.append(geo.fill_with_holes(floor_poly, [geo.circle(dx, dy, ring_r, 48)], z=fz, name=f"{model}_floor{i}", mat=gm, collection=col))
        objs += drain(f"{model}_drain{i}", dx, dy, fz, dr["d"] / 2 * M, ring_r, col)
    if model == "GST 7546":
        objs += gst7546_fittings(fittings_colour or colour, col)
    for o in objs:
        o["sink"] = model
    return dict(objects=objs, cutout=cutout(model), mount=g["mount"], flange=flange, outline=out, size=(W * M, D * M), depth=Dz)


def _raised_floor_left(model, floor_poly, step, gm, col, fz):
    """GST 7546's floor: the part left of the step line stands 2 mm higher than the drain's part."""
    sx, sy, sr, h = step["x"] * M, -step["z"] * M, step["r"] * M, step["h"] * M
    ys = [p[1] for p in floor_poly]
    y_lo, y_hi = min(ys), max(ys)
    n = len(floor_poly)
    left = [x < sx for x, _ in floor_poly]
    # the ring is CCW (front edge rightwards, right side, back edge leftwards, left side): the points left of the
    # step form one run, which starts where the back edge crosses x = sx
    start = next(i for i in range(n) if left[i] and not left[i - 1])
    run = []
    i = start
    while left[i]:
        run.append(floor_poly[i])
        i = (i + 1) % n
    line = [(sx, y_lo), (sx, sy - sr)]
    for k in range(1, 24):
        a = -math.pi / 2 - math.pi * k / 24
        line.append((sx + sr * math.cos(a), sy + sr * math.sin(a)))
    line += [(sx, sy + sr), (sx, y_hi)]
    ob = geo.slab(run + line, [], fz, fz + h, name=f"{model}_floor_step", mat=gm, collection=col, bevel=0.0006, bevel_segments=2)
    return [ob]


def drain(name, x, y, z, r_cap, r_ring, col):
    """A spun steel cap over a dark ring, as in the photographs."""
    objs = []
    dark = mats.rubber_dark()
    objs.append(geo.cylinder(x, y, z - 0.02, z - 0.0005, r_ring, 48, name=name + "_well", mat=dark, collection=col))
    cap = geo.lathe([(0.0, 0.0045), (r_cap * 0.6, 0.0042), (r_cap * 0.95, 0.0033), (r_cap, 0.0024), (r_cap, 0.0008), (r_cap * 0.97, 0.0)],
                    n=72, name=name + "_cap", mat=mats.spun_steel(), collection=col, cx=0.0, cy=0.0, z=0.0)
    cap.location = (x, y, z)
    objs.append(cap)
    return objs


def gst7546_fittings(colour, col):
    """GST 7546's deck, as photographed: the glass rinser, the pull-out spray, the faucet, the control knob and the
    drain button, along the back deck. Heights are not visible from above: typical values."""
    objs = []
    fit = mats.metal("black") if colour == "pearl" else (mats.metal("white") if colour == "pure" else mats.metal("gunmetal"))
    steel = mats.metal("steel")
    rub = mats.rubber_dark()
    y = lambda z: -z * M
    # glass rinser: a steel ring, black petals
    rx, ry = -294 * M, y(-195)
    objs.append(geo.lathe([(0.0, 0.012), (0.048, 0.012), (0.054, 0.010), (0.054, 0.0), (0.0, 0.0)], n=64, name="rinser", mat=steel, collection=col, cx=rx, cy=ry))
    objs.append(geo.cylinder(rx, ry, 0.0121, 0.0128, 0.047, 64, name="rinser_face", mat=rub, collection=col))
    for k in range(6):
        a = math.radians(90 + 60 * k)
        px, py = rx + 0.026 * math.cos(a), ry + 0.026 * math.sin(a)
        ob = geo.box(-0.016, -0.005, 0.0, 0.016, 0.005, 0.004, name="petal", mat=mats.metal("gunmetal"), collection=col, bevel=0.002)
        ob.location = (px, py, 0.0128)
        ob.rotation_euler = (0, 0, a)
        objs.append(ob)
    objs.append(geo.cylinder(rx, ry, 0.0128, 0.0175, 0.007, 32, name="rinser_boss", mat=steel, collection=col, bevel=0.001))
    # pull-out spray: a small round head on the deck, its wand lying forward
    objs.append(geo.cylinder(-137 * M, y(-195), 0.0, 0.012, 0.016, 32, name="spray_base", mat=fit, collection=col, bevel=0.002))
    objs.append(geo.tube([(-137 * M, y(-195) - 0.004, 0.006), (-137 * M, y(-195) - 0.05, 0.006)], 0.0035, 12, name="spray_wand", mat=fit, collection=col))
    # faucet: a pull-down gooseneck rising from the deck, its spout over the bowl
    objs += faucet_gooseneck("gst_faucet", 0.0, y(-197), 0.0, height=0.33, reach=0.20, r=0.0105, base_r=0.0205, mat=fit, col=col)
    # control knob and drain button
    objs.append(geo.cylinder(77 * M, y(-195), 0.0, 0.016, 0.018, 40, name="knob", mat=fit, collection=col, bevel=0.002))
    objs.append(geo.cylinder(326 * M, y(-197), 0.0, 0.004, 0.018, 40, name="drain_btn", mat=steel, collection=col, bevel=0.0012))
    # the waterfall outlet: a perforated strip along the back, just below the rim
    for k in range(40):
        x = (116 + (300 - 116) * (k + 0.5) / 40) * M
        objs.append(geo.box(x - 0.0016, y(-155.6) - 0.0018, -0.0016, x + 0.0016, y(-155.6) + 0.0018, -0.0004, name="outlet_slot", mat=rub, collection=col))
    return objs


def faucet_gooseneck(name, x, y, z, height=0.33, reach=0.2, r=0.011, base_r=0.02, mat=None, col=None, turn=0.0):
    """A gooseneck faucet: a round base, a column, an arc forward and a spout pointing down."""
    objs = []
    objs.append(geo.cylinder(x, y, z, z + 0.012, base_r, 48, name=name + "_base", mat=mat, collection=col, bevel=0.002))
    pts = []
    top = z + height
    col_top = top - reach * 0.5
    pts.append((x, y, z + 0.010))
    pts.append((x, y, col_top))
    # arc from vertical to pointing down, centre forward of the column
    R = reach / 2
    cy = y - R
    for k in range(1, 25):
        a = math.pi * k / 24
        pts.append((x, y - R + R * math.cos(a), col_top + R * math.sin(a)))
    end = pts[-1]
    pts.append((end[0], end[1], end[2] - 0.06))
    objs.append(geo.tube(pts, r, 24, name=name + "_neck", mat=mat, collection=col))
    return objs
