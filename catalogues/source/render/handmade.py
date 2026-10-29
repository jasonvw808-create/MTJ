"""The fourteen hand made stainless steel sinks (wellup): a flat deck plate, square-walled bowls with
ledges front and back, floors falling to the waste in four planes, and the fittings the
photographs show on each deck. Measurements: steel_data.STEEL.

The installation follows the model code's letter after the size, read the same way as the
granite range's (T top-mount, U undermount) — the price list itself does not state it."""
import math
import numpy as np
import bpy
from . import geo, mats
from .steel_data import STEEL, H

M = 0.001


def _rect_m(rect):
    x0, x1, z0, z1 = rect
    return x0 * M, x1 * M, -z1 * M, -z0 * M


def mount_of(model):
    code = model.split()[-1]
    return "under" if code.startswith("U") else "top"


def bowl(name, rect, r, depth, drain, finish_mat, col, ledges=True, lip=None, top_z=0.0, overflow=None, outlet=None, plate=0.003):
    """One square-walled bowl, lofted from the deck down: the lip, the wall (a ledge front and back), the
    floor round, and the floor falling to the waste in four planes."""
    x0, x1, y0, y1 = rect
    lip = (lip if lip is not None else H["lip"]) * M
    D = depth * M
    fR = H["floorR"] * M
    fall = H["fall"] * M
    nc, ns = 8, (24, 14)
    rings = []

    def ring(ix, iyf, iyb, z, rr):
        pts = geo.rrect(x0 + ix, x1 - ix, y0 + iyf, y1 - iyb, max(0.0008, rr), n_corner=nc, n_side=ns)
        return [(px, py, top_z + z) for (px, py) in pts]

    for k in range(5):
        th = (math.pi / 2) * k / 4
        off = lip - lip * math.sin(th)
        rings.append(ring(-off, -off, -off, -lip + lip * math.cos(th), r * M + off))
    led = H["ledge"] if ledges else None
    if led:
        zd, w = -led["drop"] * M, led["w"] * M
        rings.append(ring(0, 0, 0, zd + 0.0012, r * M))
        # the ledge: a small round, across, a small round, down
        rings.append(ring(0, 0.0008, 0.0008, zd + 0.0001, r * M))
        rings.append(ring(0, w - 0.0008, w - 0.0008, zd, r * M))
        rings.append(ring(0, w, w, zd - 0.0012, r * M))
        iy = w
    else:
        iy = 0.0
    zf = -(D - fR)
    rings.append(ring(0, iy, iy, zf, r * M))
    for k in range(1, 6):
        th = (math.pi / 2) * k / 5
        add = fR - fR * math.cos(th)
        rings.append(ring(add, iy + add, iy + add, zf - fR * math.sin(th), max(0.002, r * M - add * 0.5)))
    ob = geo.loft(rings, name=name, mat=finish_mat, collection=col, smooth_angle=50)
    objs = [ob]
    # floor: from its edge to the waste, four planes meeting on the diagonals
    last = rings[-1]
    dx, dy = drain["x"] * M, -drain["z"] * M
    rw = drain["d"] / 2 * M
    fx0, fx1 = min(p[0] for p in last), max(p[0] for p in last)
    fy0, fy1 = min(p[1] for p in last), max(p[1] for p in last)
    zfloor = top_z - D

    def fz(x, y):
        px = (x - dx) / (fx1 - dx) if x >= dx else (dx - x) / (dx - fx0)
        py = (y - dy) / (fy1 - dy) if y >= dy else (dy - y) / (dy - fy0)
        m = max(min(px, 1.0), min(py, 1.0))
        return zfloor - fall * (1 - m)

    n_in = 10
    frings = []
    edge = [(p[0], p[1]) for p in last]
    for k in range(n_in + 1):
        t = k / n_in
        rr = []
        for (ex, ey) in edge:
            # point on the waste's ring in the same direction
            ang = math.atan2(ey - dy, ex - dx)
            qx, qy = dx + rw * math.cos(ang), dy + rw * math.sin(ang)
            x = ex + (qx - ex) * t
            y = ey + (qy - ey) * t
            rr.append((x, y, fz(x, y) if k > 0 else zfloor))
        frings.append(rr)
    objs.append(geo.loft(frings, name=name + "_floor", mat=finish_mat, collection=col, smooth_angle=8))
    # the waste
    objs += waste(name + "_waste", dx, dy, zfloor - fall, rw, drain.get("type", "basket"), col)
    # overflow slots on the back wall, under the deck
    if overflow:
        for x in overflow:
            objs.append(geo.box(x * M - 0.0035, y1 - 0.0004, top_z - 0.020, x * M + 0.0035, y1 + 0.002, top_z - 0.012, name=name + "_ovf", mat=mats.rubber_dark(), collection=col, bevel=0.0012))
    if outlet:
        a, b = outlet
        objs.append(geo.box(a * M, y1 - 0.0005, top_z - 0.022, b * M, y1 + 0.003, top_z - 0.016, name=name + "_outlet", mat=mats.rubber_dark(), collection=col, bevel=0.001))
    return objs, (x0, x1, y0, y1)


def waste(name, x, y, z, r, kind, col):
    objs = []
    steel = mats.metal("steel")
    if kind == "popup":
        objs.append(geo.lathe([(0.0, 0.007), (r * 0.75, 0.0065), (r * 0.97, 0.004), (r * 1.0, 0.001), (r * 1.06, 0.0)], n=64,
                              name=name, mat=mats.spun_steel(), collection=col, cx=0, cy=0, z=0))
        objs[-1].location = (x, y, z)
        return objs
    # basket strainer: steel flange, perforated basket, a central knob
    objs.append(geo.lathe([(r * 0.86, 0.0), (r * 0.86, 0.003), (r * 1.08, 0.003), (r * 1.14, 0.0)], n=64, name=name + "_flange", mat=steel, collection=col, cx=x, cy=y, z=z))
    objs.append(geo.lathe([(r * 0.86, 0.002), (r * 0.82, -0.025), (r * 0.66, -0.05), (0.0, -0.052)], n=48, name=name + "_basket", mat=mats.perforated(base=(0.55, 0.55, 0.55)), collection=col, cx=x, cy=y, z=z))
    objs.append(geo.cylinder(x, y, z - 0.052, z + 0.012, 0.006, 24, name=name + "_post", mat=steel, collection=col, bevel=0.002))
    objs.append(geo.cylinder(x, y, z - 0.09, z - 0.06, r * 0.9, 24, name=name + "_dark", mat=mats.rubber_dark(), collection=col))
    return objs


def fittings(d, mat_body, col, top_z=0.0, black=False):
    objs = []
    chrome = mats.metal("chrome")
    steel = mats.metal("steel")
    blk = mats.metal("black")
    whitep = mats.plastic((0.85, 0.85, 0.83), 0.3)
    for f in d["fittings"]:
        k = f["kind"]
        if k == "knife":
            x0, x1, y0, y1 = _rect_m([f["x0"], f["x1"], f["z0"], f["z1"]])
            h = f["h"] * M
            objs.append(geo.box(x0, y0, top_z, x1, y1, top_z + h, name="knife", mat=steel, collection=col, bevel=0.0012))
            # the slots: four long, one short at the end
            L = x1 - x0
            for j in range(4):
                yy = y0 + (y1 - y0) * (0.22 + 0.19 * j)
                objs.append(geo.box(x0 + L * 0.06, yy - 0.0014, top_z + h - 0.003, x0 + L * (0.78 if j % 2 == 0 else 0.62), yy + 0.0014, top_z + h + 0.0002, name="knife_slot", mat=mats.rubber_dark(), collection=col))
            objs.append(geo.box(x0 + L * 0.86, y0 + (y1 - y0) * 0.22, top_z + h - 0.003, x0 + L * 0.93, y0 + (y1 - y0) * 0.78, top_z + h + 0.0002, name="knife_slot2", mat=mats.rubber_dark(), collection=col, bevel=0.002))
        elif k == "dispenser":
            x, y, r = f["x"] * M, -f["z"] * M, f["d"] / 2 * M
            objs.append(geo.lathe([(0.0, 0.016), (r * 0.62, 0.0158), (r * 0.9, 0.0135), (r, 0.009), (r, 0.0), (0.0, 0.0)], n=64, name="dispenser", mat=chrome, collection=col, cx=x, cy=y, z=top_z))
            objs.append(geo.lathe([(r * 1.04, 0.0), (r * 1.04, 0.0025), (r * 0.98, 0.003)], n=64, name="dispenser_ring", mat=chrome, collection=col, cx=x, cy=y, z=top_z))
        elif k == "knob":
            # as photographed: a round top on a short column, with a thin rod reaching forward over the bowl
            x, y, r = f["x"] * M, -f["z"] * M, f["d"] / 2 * M
            hcol = 0.040
            objs.append(geo.lathe([(r * 0.92, 0.0), (r * 0.92, 0.003), (r * 0.62, 0.004), (r * 0.62, hcol - 0.010), (r * 0.98, hcol - 0.008), (r, hcol - 0.004), (r * 0.94, hcol), (0.0, hcol)],
                                  n=64, name="knob", mat=steel, collection=col, cx=x, cy=y, z=top_z))
            objs.append(geo.tube([(x, y - r * 0.6, top_z + hcol - 0.006), (x, y - 0.115, top_z + hcol - 0.010), (x, y - 0.118, top_z + hcol - 0.030)], 0.0034, 14, name="knob_rod", mat=steel, collection=col))
        elif k == "rinser":
            x, y, r = f["x"] * M, -f["z"] * M, f["d"] / 2 * M
            objs.append(geo.lathe([(0.0, 0.0), (r, 0.0), (r, 0.009), (r * 0.9, 0.010), (r * 0.9, 0.006), (0.0, 0.006)], n=64, name="rinser", mat=steel, collection=col, cx=x, cy=y, z=top_z))
            objs.append(geo.cylinder(x, y, top_z + 0.0055, top_z + 0.0075, r * 0.86, 64, name="rinser_face", mat=mats.rubber_dark(), collection=col))
            for j in range(6):
                a = math.radians(30 + 60 * j)
                ob = geo.box(-0.013, -0.0045, 0.0, 0.013, 0.0045, 0.003, name="petal", mat=mats.metal("gunmetal"), collection=col, bevel=0.0015)
                ob.location = (x + 0.021 * math.cos(a), y + 0.021 * math.sin(a), top_z + 0.0075)
                ob.rotation_euler = (0, 0, a)
                objs.append(ob)
        elif k == "block":
            x0, x1, y0, y1 = _rect_m([f["x0"], f["x1"], f["z0"], f["z1"]])
            yb = f.get("y", 0) * M
            m = {"black": blk, "steel": steel}.get(f.get("part"), blk)
            objs.append(geo.box(x0, y0, top_z + yb, x1, y1, top_z + yb + f["h"] * M, name="block", mat=m, collection=col, bevel=0.0025 if f["h"] > 5 else 0.0008))
        elif k == "round":
            x, y, r = f["x"] * M, -f["z"] * M, f["d"] / 2 * M
            yb = f.get("y", 0) * M
            m = {"yellow": mats.plastic((0.85, 0.62, 0.05), 0.35), "white": whitep, "black": blk}.get(f.get("part"), steel)
            objs.append(geo.cylinder(x, y, top_z + yb, top_z + yb + f["h"] * M, r, 48, name="round", mat=m, collection=col, bevel=0.0015))
        elif k == "inlay":
            x0, x1, y0, y1 = _rect_m([f["x0"], f["x1"], f["z0"], f["z1"]])
            yb = f.get("y", 0) * M
            objs.append(geo.box(x0, y0, top_z + yb, x1, y1, top_z + yb + 0.0006, name="display", mat=mats.lcd(), collection=col))
        elif k == "faucet":
            from .props import faucet_pulldown
            x, y = f["x"] * M, -f["z"] * M
            yb = f.get("y", 0) * M
            objs += faucet_pulldown("spray", x, y, top_z + yb, height=f["h"] * M, reach=f["reach"] * M, mat=blk, col=col)
        elif k == "tapring":
            x, y, r = f["x"] * M, -f["z"] * M, f["d"] / 2 * M
            objs.append(geo.lathe([(r * 0.6, 0.0), (r * 0.6, 0.0015), (r, 0.0015), (r * 1.02, 0.0)], n=64, name="tapring", mat=steel, collection=col, cx=x, cy=y, z=top_z))
            objs.append(geo.cylinder(x, y, top_z - 0.02, top_z + 0.0001, r * 0.6, 32, name="taphole", mat=mats.rubber_dark(), collection=col))
        elif k == "pane":
            pass  # built with the recesses
    return objs


def build(model, col=None):
    d = STEEL[model]
    W, D = d["size"][0] * M, d["size"][1] * M
    cr = d["cornerR"] * M
    plate = d.get("plate", 3) * M
    edgeR = H["edgeR"] * M
    mat = mats.steel(d["finish"])
    mount = mount_of(model)
    objs = []
    holes = []
    outline = geo.rrect(-W / 2, W / 2, -D / 2, D / 2, cr, n_corner=12, n_side=(30, 18))
    bowl_rects = []
    seat = plate   # how far the sink's top stands above the worktop it rests on
    if d.get("top") == "glass":
        # W 10050 TSG: a black glass top over a satin body; the bowl under an opening in the glass, the wing grooved
        op = d["opening"]
        gx0, gx1, gy0, gy1 = _rect_m(op["rect"])
        gp = d["glass_plate"] * M
        seat = gp + plate   # the glass on the body, the body on the worktop
        open_pts = geo.rrect(gx0, gx1, gy0, gy1, op["r"] * M, n_corner=10, n_side=(24, 14))
        glass = geo.slab(outline, [open_pts], -gp, 0.0, name=model + "_glass", mat=mats.black_glass(), collection=col, bevel=0.0025, bevel_segments=2)
        objs.append(glass)
        # the satin flange inside the opening, 6 mm down
        b = op["bowl"]
        bx0, bx1, by0, by1 = _rect_m(b["shape"]["rect"])
        inner = geo.rrect(bx0 - H["lip"] * M, bx1 + H["lip"] * M, by0 - H["lip"] * M, by1 + H["lip"] * M, b["shape"]["r"] * M + H["lip"] * M, n_corner=8, n_side=(24, 14))
        objs.append(geo.fill_with_holes(geo.rrect(gx0 - 0.002, gx1 + 0.002, gy0 - 0.002, gy1 + 0.002, op["r"] * M + 0.002), [inner], z=-gp, name=model + "_flange", mat=mat, collection=col))
        bo, rc = bowl(model + "_bowl", (bx0, bx1, by0, by1), b["shape"]["r"], b["depth"], b["drain"], mat, col, ledges=True, top_z=-gp)
        objs += bo
        bowl_rects.append(rc)
        # the wing's grooves: thin dark lines cut into the glass
        for g in d["grooves"]:
            y = -g["z"] * M
            pts = []
            n = 14
            for i in range(n + 1):
                t = i / n
                x = (g["x0"] + (g["x1"] - g["x0"]) * t) * M
                w = (g["w0"] + (g["w2"] - g["w0"]) * t) * M
                pts.append((x, w))
            poly = [(x, y + w) for x, w in pts] + [(x, y - w) for x, w in reversed(pts)]
            objs.append(geo.fill_with_holes(poly, [], z=0.00005, name=model + "_groove", mat=mats.metal("gunmetal"), collection=col))
        # the body's edge under the glass
        objs.append(geo.slab(outline, [open_pts], -gp - plate, -gp, name=model + "_body", mat=mat, collection=col, bevel=0.0006))
        objs += fittings(d, mat, col, top_z=0.0)
        top_out = outline
    elif d.get("recesses"):
        # W 8550 TDG: two recesses in the frame, each holding a tempered glass cover over its bowl
        rec_pts = []
        for rc in d["recesses"]:
            x0, x1, y0, y1 = _rect_m(rc["rect"])
            rec_pts.append(geo.rrect(x0, x1, y0, y1, rc["r"] * M, n_corner=8, n_side=(24, 14)))
        objs.append(geo.fill_with_holes(geo.rrect(-W / 2 + edgeR, W / 2 - edgeR, -D / 2 + edgeR, D / 2 - edgeR, cr - edgeR), rec_pts, z=0.0, name=model + "_deck", mat=mat, collection=col))
        for i, rc in enumerate(d["recesses"]):
            x0, x1, y0, y1 = _rect_m(rc["rect"])
            dep = rc["depth"] * M
            # the recess walls and its ledge
            rings = [[(x, y, 0.0) for x, y in rec_pts[i]], [(x, y, -dep) for x, y in rec_pts[i]]]
            objs.append(geo.loft(rings, name=model + "_recess", mat=mat, collection=col, smooth_angle=40))
            # the glass cover lying on the ledge, 5.5 mm thick
            px0, px1, py0, py1 = _rect_m([[-409, 0, -170, 211], [6, 414, -170, 211]][i])
            pane = geo.rrect(px0, px1, py0, py1, 0.004, n_corner=6, n_side=(10, 6))
            objs.append(geo.slab(pane, [], -dep, -dep + 0.0055, name=model + "_cover", mat=mats.black_glass(), collection=col, bevel=0.0012, bevel_segments=2))
            # the bowl below (hidden by the cover): a dark well so nothing shows through the joints
            objs.append(geo.box(x0 + 0.002, y0 + 0.002, -0.22, x1 - 0.002, y1 - 0.002, -dep - 0.0005, name=model + "_well", mat=mats.rubber_dark(), collection=col))
            bowl_rects.append((x0, x1, y0, y1))
        objs += fittings(d, mat, col, top_z=0.0)
        top_out = outline
    else:
        for i, b in enumerate(d["bowls"]):
            x0, x1, y0, y1 = _rect_m(b["shape"]["rect"])
            r = b["shape"]["r"]
            lip = H["lip"] * M
            holes.append(geo.rrect(x0 - lip, x1 + lip, y0 - lip, y1 + lip, r * M + lip, n_corner=8, n_side=(24, 14)))
            bo, rc = bowl(f"{model}_bowl{i}", (x0, x1, y0, y1), r, b["depth"], b["drain"], mat, col, ledges=bool(b.get("ledges")),
                          overflow=b.get("overflow"), outlet=b.get("outlet"))
            objs += bo
            bowl_rects.append(rc)
        deck_out = geo.rrect(-W / 2 + edgeR, W / 2 - edgeR, -D / 2 + edgeR, D / 2 - edgeR, max(0.001, cr - edgeR), n_corner=12, n_side=(30, 18))
        objs.append(geo.fill_with_holes(deck_out, holes, z=0.0, name=model + "_deck", mat=mat, collection=col))
        objs += fittings(d, mat, col, top_z=0.0)
    # the plate's edge: a small round, then straight down its thickness
    rings = []
    for k in range(5):
        th = (math.pi / 2) * k / 4
        off = edgeR - edgeR * math.sin(th)
        pts = geo.rrect(-W / 2 + off, W / 2 - off, -D / 2 + off, D / 2 - off, max(0.0008, cr - off), n_corner=12, n_side=(30, 18))
        rings.append([(x, y, -edgeR + edgeR * math.cos(th)) for x, y in pts])
    pts = geo.rrect(-W / 2, W / 2, -D / 2, D / 2, cr, n_corner=12, n_side=(30, 18))
    rings.append([(x, y, -plate) for x, y in pts])
    if d.get("top") != "glass":
        objs.append(geo.loft(rings, name=model + "_edge", mat=mat, collection=col, smooth_angle=50, flip=True))
    for o in objs:
        o["sink"] = model
    # the countertop's cut-out
    if mount == "under":
        rx0 = min(r[0] for r in bowl_rects) - 0.003
        rx1 = max(r[1] for r in bowl_rects) + 0.003
        ry0 = min(r[2] for r in bowl_rects) - 0.003
        ry1 = max(r[3] for r in bowl_rects) + 0.003
        rr = (d["bowls"][0]["shape"]["r"] + 3) * M
        cut = [geo.rrect(rx0, rx1, ry0, ry1, rr)]
    else:
        # the rim rests on the worktop round a cut-out 20 mm in from its edge, or wider where a bowl or recess reaches
        # further out (W 7546 TSBN, W 8550 TDG): nothing of the sink passes through the stone
        cx0 = min([-W / 2 + 0.02] + [r[0] - 0.003 for r in bowl_rects])
        cx1 = max([W / 2 - 0.02] + [r[1] + 0.003 for r in bowl_rects])
        cy0 = min([-D / 2 + 0.02] + [r[2] - 0.003 for r in bowl_rects])
        cy1 = max([D / 2 - 0.02] + [r[3] + 0.003 for r in bowl_rects])
        cut = [geo.rrect(cx0, cx1, cy0, cy1, 0.008)]
    return dict(objects=objs, cutout=cut, mount=mount, flange=seat, outline=outline, size=(W, D), depth=d["height"] * M)
